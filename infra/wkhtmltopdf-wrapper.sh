#!/bin/sh
exec xvfb-run --server-args="-screen 0 1024x768x24" /usr/bin/wkhtmltopdf --enable-local-file-access "$@"
