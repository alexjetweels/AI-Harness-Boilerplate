# I. Tạo mới 
## step 1: gen wide system srs
 - use agent: 　okr.srsallsystem
 - Prompt
> Generate system-wide SRS (Full Module Requirements Definition) for the OKR web app base on input at docs/input/okr-requirement.md

## step 2: chọn module sẽ tạo
### a. Case run from vscode
 - use agent: 　`okr.bossbuiltin`
 - Prompt
 > {MODxx: tên module}
    
### b. Case run from copilot CLI
 - use agent: 　`okr.bossbuiltin`
 - Prompt
 > execute the full pipeline for {MODxx: tên module}

# II. Change spec
## step 3: thực hiện CR cho 1 module
 - Prompt
> execute an UPDATE pipeline for change requests at docs/input/change-request/change-0405.md for MOD-02: Workspace & Dashboard