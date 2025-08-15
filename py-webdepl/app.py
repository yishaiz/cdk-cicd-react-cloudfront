#!/usr/bin/env python3
import os

import aws_cdk as cdk

from py_webdepl.py_webdepl_stack import PyWebdeplStack


app = cdk.App()
PyWebdeplStack(app, "PyWebdeplStack")

app.synth()
