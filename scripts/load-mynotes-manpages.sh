#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAN_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/man/man1"
MAN_FILE="$MAN_DIR/mynotes.1"

mkdir -p "$MAN_DIR"

cat > "$MAN_FILE" <<'EOF'
.TH MYNOTES 1 "2026-07-21" "MyNotes" "User Commands"
.SH NAME
mynotes \- schedule desktop notifications from the command line
.SH SYNOPSIS
.B mynotes
[IstartR|IstopR|IrestartR|IshowR|IstatusR|IcheckR|IcancelR|IpurgeR|IclearR|ItextR]
.SH DESCRIPTION
MyNotes is a small helper for queuing short reminders as desktop notifications.
It uses a background service to monitor a work queue and display notes when their
scheduled time arrives.
.PP
Common commands:
.TP
.B start
Launch the MyNotes background service.
.TP
.B stop
Stop the background service.
.TP
.B restart
Restart the background service.
.TP
.B show
Display pending notes from the database.
.TP
.B status
Check whether the service is running.
.TP
.B cancel \fInameR
Cancel a pending note by name.
.TP
.B purge
Remove all notes from the database.
.TP
.B clear
Clear queued notes and input files.
.TP
.B \fItextR
Schedule a note with the provided message text.
.SH EXAMPLES
.PP
mynotes start
.PP
mynotes "Take a break"
.PP
mynotes cancel 3
.SH SEE ALSO
The project README and the shell wrapper in the repository.
EOF

if command -v mandb >/dev/null 2>&1; then
    mandb 2>/dev/null || true
fi

echo "Installed man page to $MAN_FILE"
