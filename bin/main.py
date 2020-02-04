import collections
import itertools
import os
import sys
import traceback

import errno
from os.path import dirname, realpath
from os.path import join as pathjoin
from fcntl import flock, LOCK_EX, LOCK_NB
from os import O_RDWR, O_CREAT, O_WRONLY, O_APPEND


class BootstrapMain:
    def _load_config(self, *args, **kwargs):
        try:
            base_path = self.find_install_path(sys.argv[0])
        except Exception as e:
            print("ERROR: {}".format(e))
            sys.exit(1)
        self._bootstrap_cfg = realpath(pathjoin(base_path, "bin/config.properties"))
        self._jvm_cfg = realpath(pathjoin(base_path, "etc/jvm.config"))
        self._app_cfg = realpath(pathjoin(base_path, "etc/config.properties"))
        self._log_cfg = realpath(pathjoin(base_path, "etc/log.properties"))
        self._pid_cfg = realpath(pathjoin(base_path, "var/run/launcher.pid"))
        self._bootstrap_log_cfg = realpath(pathjoin(base_path, "var/log/launcher.log"))
        self._app_log_cfg = realpath(pathjoin(base_path, "var/log/server.log"))
        self._etc_dir_cfg = realpath(pathjoin(base_path, "etc"))
        self._base = realpath(base_path)
        self._log_set = True

    def __init__(self, *args, **kwargs):
        self._load_config(*args, **kwargs)

        path = self._pid_cfg
        self.makedirs(dirname(path))
        self.path = path

        def _fs(f, s):
            return os.fdopen(os.open(f, O_CREAT | O_RDWR, s), "r+")

        self._ps = _fs(path, 0o600)
        self.acquire()

    # todo thread safe
    def acquire(self):
        self._locked = self.try_lock(self._ps)

    def release(self):
        raise NotImplementedError

    def clear(self):
        self._ps.seek(0)
        self._ps.truncate()

    def write(self, pid):
        self.clear()
        self._ps.write(str(pid) + "\n")
        self._ps.flush()

    def check(self):
        self.acquire()
        if self._locked:
            return False

        pid = self.read()
        os.kill(pid, 0)
        return True

    def read(self):
        self._ps.seek(0)
        line = self._ps.readline().strip()
        return int(line)

    @classmethod
    def redirect(cls):
        fd = os.open(os.devnull, O_RDWR)
        os.dup2(fd, sys.stdin.fileno())
        os.close(fd)

    @classmethod
    def open_append(cls, f):
        return os.open(f, O_WRONLY | O_APPEND | O_CREAT, 0o644)

    def prepare_exec(self):
        properties = collections.OrderedDict()
        main_class = self.parse_properties(self._bootstrap_cfg)["main-class"]
        properties["log.levels-file"] = self._log_cfg
        properties["config"] = self._app_cfg
        classpath = pathjoin(self._base, "lib", "*")

        def merge(*args):
            e = {}
            for vs in itertools.zip_longest(*args, fillvalue=e):
                for v in vs:
                    if vs is not e:
                        yield v

        cur = (
            ["java", "-cp", classpath]
            + self.parse_lines(self._jvm_cfg)
            + ["-D%s=%s" % i for i in properties.items()]
            + [main_class]
        )
        env = os.environ.copy()
        return cur, env

    @classmethod
    def find_install_path(cls, f):
        return dirname(realpath(dirname(f)))

    @classmethod
    def makedirs(cls, p):
        try:
            os.makedirs(p)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    @classmethod
    def parse_properties(cls, f):
        return dict(x.split("=", 1) for x in (y.strip() for y in cls.parse_lines(f)))

    @classmethod
    def parse_lines(cls, f):
        return list(
            filter(
                lambda x: len(x) > 0 and not x.startswith("#"),
                map(lambda y: y.strip(), open(f, "r").readlines()),
            )
        )

    @classmethod
    def try_lock(cls, f):
        try:
            flock(f, LOCK_EX | LOCK_NB)
            return True
        except (IOError, OSError):
            return False

    def run(self):
        if self.check():
            return
        else:
            args, env = self.prepare_exec()
            self.makedirs(self._base)
            os.chdir(self._base)
            self.write(os.getpid())
            self.redirect()
            os.execvpe(args[0], args, env)


def main():
    try:
        bootstrap = BootstrapMain()
        bootstrap.run()
    except:
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
