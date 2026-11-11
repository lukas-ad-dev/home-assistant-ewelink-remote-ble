from custom_components.ewelink_remote_ble import _decode


def test_known_r5_packet():
    raw = bytes.fromhex(
        "0201021B05FFFFEE1BC878F64A4790365AD509227B7442C5245C7DE4828B98"
    )
    assert _decode(raw) == {
        "device_id": "5AD50922",
        "device_type": "R5",
        "button": 1,
        "action": "single",
        "counter": 150,
    }
