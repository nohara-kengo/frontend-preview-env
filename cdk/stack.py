#!/usr/bin/env python3
"""
AWS CDK Stack Definition
"""

from aws_cdk import core

class MyStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        # TODO: リソース定義をここに記述

class MyApp(core.App):
    def __init__(self):
        super().__init__()
        MyStack(self, "MyStack")

if __name__ == "__main__":
    app = MyApp()
    app.synth()
