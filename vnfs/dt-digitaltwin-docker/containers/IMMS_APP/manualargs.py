import argparse
#
# Command line argument parser
#
def parse_args(manual_args=None):
    """
    CLI interface definition.
    """
    parser = argparse.ArgumentParser(
        description="IMMS ('Injection Molding Machine Simulator' Application)")

    parser.add_argument(
        "-a",
        "--autostart",
        help="Automatically start production.",
        required=False,
        default=False,
        dest="autostart",
        action="store_true")

    parser.add_argument(
        "-p",
        "--playback",
        help="Playback of production data recorded.",
        required=False,
        default=False,
        dest="playback",
        action="store_true")

    parser.add_argument(
        "--varATActSimPara1",
        required=False,
        default=5)

    parser.add_argument(
        "--varATActSimPara2period",
        required=False,
        default=20.0)

    parser.add_argument(
        "--varATActSimPara2amplitude",
        required=False,
        default=1.0)

    parser.add_argument(
        "--varATActSimPara2phase",
        required=False,
        default=0)

    parser.add_argument(
        "--varATActSimPara2offset",
        required=False,
        default=1.0)

    parser.add_argument(
        "--varPlotATActSimPara",
        required=False,
        default=False)

    parser.add_argument(
        "--varSetCntMld",
        required=False,
        default=10)

    parser.add_argument(
        "--varSetCntPrt",
        required=False,
        default=10000)

    parser.add_argument(
        "--varSetTimCyc",
        required=False,
        default=5.0)

    parser.add_argument(
        "--enableOPCUA",
        help="Enable OPC UA client.",
        required=False,
        default=False,
        dest="enableOPCUA",
        action="store_true")

    parser.add_argument(
        "--enablePi3",
        help="Enable RGB LED control via Raspberry Pi 3 GPIOs.",
        required=False,
        default=False,
        dest="enablePi3",
        action="store_true")

    parser.add_argument(
        "--enable5inchTouch",
        help="Enable optimized web gui for 5 inch touch screen.",
        required=False,
        default=False,
        dest="enable5inchTouch",
        action="store_true")

    parser.add_argument(
        "--disableSamba",
        help="Disable Euromap 63 via Samba. Default share: ../em63_share/.",
        required=False,
        default=False,
        dest="disableSamba",
        action="store_true")

    if manual_args is not None:
        return parser.parse_args(manual_args)
    return parser.parse_args()
