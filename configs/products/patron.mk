# Unipi Patron — a PLC built on the Unipi Zulu (i.MX8M Mini), so it reuses the
# Zulu fragment set. Recursive (deferred) assignment so include order is free.
patron_ARCH      := arm64
patron_Fragments  = $(zulu_Fragments)
