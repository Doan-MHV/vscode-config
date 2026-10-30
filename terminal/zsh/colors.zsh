# shellcheck disable=SC2034,SC2190,SC2206,SC2296
# Lantern District terminal syntax & file icon colors (matches Antigravity IDE 1.4.0)

typeset -A ZSH_HIGHLIGHT_REGEXP
typeset -A ZSH_HIGHLIGHT_STYLES
ZSH_HIGHLIGHT_HIGHLIGHTERS=(main regexp)

ZSH_HIGHLIGHT_STYLES[default]='fg=#ECE4DC'
ZSH_HIGHLIGHT_STYLES[unknown-token]='fg=#E87D72,bold'
ZSH_HIGHLIGHT_STYLES[reserved-word]='fg=#C4A7E7,bold'
ZSH_HIGHLIGHT_STYLES[alias]='fg=#F2A365'
ZSH_HIGHLIGHT_STYLES[suffix-alias]='fg=#F2A365'
ZSH_HIGHLIGHT_STYLES[global-alias]='fg=#F2A365'
ZSH_HIGHLIGHT_STYLES[builtin]='fg=#F2A365'
ZSH_HIGHLIGHT_STYLES[function]='fg=#F2A365'
ZSH_HIGHLIGHT_STYLES[command]='fg=#F2A365'
ZSH_HIGHLIGHT_STYLES[precommand]='fg=#C4A7E7'
ZSH_HIGHLIGHT_STYLES[commandseparator]='fg=#8BD5CA'
ZSH_HIGHLIGHT_STYLES[hashed-command]='fg=#F2A365'
ZSH_HIGHLIGHT_STYLES[path]='fg=#89B4FA,underline'
ZSH_HIGHLIGHT_STYLES[globbing]='fg=#EBC47A'
ZSH_HIGHLIGHT_STYLES[history-expansion]='fg=#C4A7E7'
ZSH_HIGHLIGHT_STYLES[single-hyphen-option]='fg=#F28FAD'
ZSH_HIGHLIGHT_STYLES[double-hyphen-option]='fg=#F28FAD'
ZSH_HIGHLIGHT_STYLES[back-quoted-argument]='fg=#EBC47A'
ZSH_HIGHLIGHT_STYLES[single-quoted-argument]='fg=#A9C799'
ZSH_HIGHLIGHT_STYLES[double-quoted-argument]='fg=#A9C799'
ZSH_HIGHLIGHT_STYLES[dollar-quoted-argument]='fg=#A9C799'
ZSH_HIGHLIGHT_STYLES[single-quoted-argument-unclosed]='fg=#E87D72'
ZSH_HIGHLIGHT_STYLES[double-quoted-argument-unclosed]='fg=#E87D72'
ZSH_HIGHLIGHT_STYLES[redirection]='fg=#8BD5CA'
ZSH_HIGHLIGHT_STYLES[comment]='fg=#726B8A'
ZSH_HIGHLIGHT_STYLES[arg0]='fg=#F2A365'

ZSH_HIGHLIGHT_REGEXP=('^[[:blank:][:space:]]*('${(j:|:)${(Qk)ABBR_REGULAR_USER_ABBREVIATIONS}}')$' fg=#89B4FA)
ZSH_HIGHLIGHT_REGEXP+=('[[:<:]]('${(j:|:)${(Qk)ABBR_GLOBAL_USER_ABBREVIATIONS}}')$' fg=#C4A7E7)

# EZA_COLORS matched to Lantern District Explorer folder & file icon palette:
# Folders: #9AA7EC (blue) | C/C++/CMake/TS/MD: #9AA7EC | Header/Go: #92C4D8 (cyan)
# C#/CSS/Kotlin: #C4A7E7 (violet) | Python/JS/JSON/YAML: #EBC47A (gold)
# Rust/Java/HTML: #F2A365 (amber) | Shell/Gradle: #A9C799 (green) | Git/Images: #E87D72 (pink)
export EZA_COLORS="\
di=1;38;2;154;167;236:\
ex=1;38;2;169;199;153:\
ln=38;2;146;196;216:\
ur=38;2;235;196;122:uw=38;2;242;163;101:ux=38;2;169;199;153:ue=38;2;169;199;153:\
gr=38;2;165;158;184:gw=38;2;165;158;184:gx=38;2;165;158;184:\
tr=38;2;114;107;138:tw=38;2;114;107;138:tx=38;2;114;107;138:\
sn=38;2;242;143;173:sb=38;2;165;158;184:\
uu=38;2;235;196;122:gu=38;2;165;158;184:\
da=38;2;146;196;216:\
ga=38;2;169;199;153:gm=38;2;242;163;101:gd=38;2;232;125;114:gv=38;2;196;167;231:gt=38;2;146;196;216:\
*.c=38;2;154;167;236:*.cpp=38;2;154;167;236:*.cc=38;2;154;167;236:*.cxx=38;2;154;167;236:\
*.h=38;2;146;196;216:*.hpp=38;2;146;196;216:*.hxx=38;2;146;196;216:\
CMakeLists.txt=38;2;154;167;236:*.cmake=38;2;154;167;236:\
*.cs=38;2;196;167;231:*.csx=38;2;196;167;231:\
*.py=38;2;235;196;122:*.ipynb=38;2;235;196;122:\
*.ts=38;2;154;167;236:*.tsx=38;2;146;196;216:*.js=38;2;235;196;122:*.jsx=38;2;146;196;216:\
*.json=38;2;235;196;122:*.jsonc=38;2;235;196;122:*.yaml=38;2;235;196;122:*.yml=38;2;235;196;122:*.toml=38;2;235;196;122:\
*.md=38;2;154;167;236:*.txt=38;2;154;167;236:\
*.html=38;2;242;163;101:*.xml=38;2;242;163;101:*.rs=38;2;242;163;101:*.java=38;2;242;163;101:\
*.css=38;2;196;167;231:*.scss=38;2;196;167;231:*.kt=38;2;196;167;231:*.kts=38;2;196;167;231:\
*.go=38;2;146;196;216:\
*.sh=38;2;169;199;153:*.zsh=38;2;169;199;153:*.bash=38;2;169;199;153:\
*.png=38;2;232;125;114:*.jpg=38;2;232;125;114:*.jpeg=38;2;232;125;114:*.svg=38;2;232;125;114:*.webp=38;2;232;125;114:\
*.lock=38;2;235;196;122:.gitignore=38;2;232;125;114"
