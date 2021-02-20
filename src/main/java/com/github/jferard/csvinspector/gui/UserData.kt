package com.github.jferard.csvinspector.gui

import java.io.File

open class UserData(val file: File)

class CodeUserData(file: File) : UserData(file)

class MetaCSVUserData(file: File) : UserData(file)