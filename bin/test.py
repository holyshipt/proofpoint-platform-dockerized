from main import BootstrapMain


def test():
    BootstrapMain.parse_properties("config.properties")
    assert 1 == 1
