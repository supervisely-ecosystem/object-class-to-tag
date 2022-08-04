<div align="center" markdown>
<img src="https://github.com/supervisely-ecosystem/object-class-to-tag/releases/download/v0.1.0/app-poster.png">

# Object Classes To Tags

<p align="center">
  <a href="#Overview">Overview</a> •
  <a href="#How-To-Run">How To Run</a>
</p>

[![](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://supervise.ly/slack)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/supervisely-ecosystem/object-class-to-tag)
[![views](https://app.supervise.ly/img/badges/views/supervisely-ecosystem/object-class-to-tag.png)](https://supervise.ly)
[![runs](https://app.supervise.ly/img/badges/runs/supervisely-ecosystem/object-class-to-tag.png)](https://supervise.ly)

</div>

## Overview

This app merges existing object classes into single one, and saves class names as tags associated with each object. 


#### Technical note.
1. If there are classes with different shapes (e.g., `Rectangle` and `Bitmap`), some output classes will be created. The new classes will be named with suffixes like `_rectangle` and `_bitmap`.
2. In the case of name conflict, existing tags may be renamed with suffix `_AUTO_RENAMED`.  



## How To Run

**Step 1**: Add app to your team from Ecosystem if it is not there.

<img src="https://github.com/supervisely-ecosystem/object-class-to-tag/releases/download/v0.1.0/shot00.png"/>

**Step 2**: Open context menu of project -> `Run App` -> `Object classes to tags` 

<img src="https://github.com/supervisely-ecosystem/object-class-to-tag/releases/download/v0.1.0/shot01.png"/>

**Step 3**: Input name of new object class and (optionally) name of output project. New project in the same workspace will be created.

<img src="https://github.com/supervisely-ecosystem/object-class-to-tag/releases/download/v0.1.0/shot02.png"  width=500px/>
