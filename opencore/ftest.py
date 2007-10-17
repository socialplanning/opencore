from toppftest import command
from opencore.configuration import OC_REQ

class ftest(command.ftest):
    requirement = OC_REQ
    description = "run flunc tests for opencore"

