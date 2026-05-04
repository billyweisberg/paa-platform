# Project Packs

Project packs hold project-specific automation and skill templates that are installed by the generic PAA platform runtime.

The platform repo owns:
- generic runtime code
- generic installers
- generic schemas
- generic command surfaces

Each project pack owns:
- project-specific skill templates
- project-specific automation templates
- a `pack.json` manifest declaring which assets belong to producer installs and consumer installs
