# Multi-project builder for jamesli.io

Using some configuration options in config.json, build.py will clone a bunch of git projects, build them, and mount them
on subdirectories of my website. The contents of the main source directory will be used as the index.

## Setting up

The build command should be `python build.py`, requiring python 3.9.

With the current `config.json` setup, the build output folder is `public`.

## `config.json` description

`outputPath` is the path to the directory with the built website

`workingPath` is the path to a directory that will be made as a scratchpad for the builder to work

`projects` is a list of project objects, with the following properties:

`projects[0].serves` is the path the given project will be served on from the website. Eg: `/` or`/my-project`

`projects[0].source` is the path to a directory or url to a git project with the source of the project.

`projects[0].buildCommands` is a list of terminal commands that will be run in the source of the project, as strings.
Eg: `["npm install", "npm run build"]`

`projects[0].buildOutput` is the folder of the eventually built project that will be copied into whereever it's served in the output.

The `serves` and `source` properties are required. A project can either have none of the build properties or all of them.