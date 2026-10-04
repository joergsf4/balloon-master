FROM debian:bookworm-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends sdcc make gcc libc6-dev git ca-certificates python3 \
 && rm -rf /var/lib/apt/lists/*

# devkitSMS (SMSlib, PSGlib, crt0). Die mitgelieferten Binaries sind x86-64 -> selbst kompilieren.
# makesms kann ROMs mit mehreren Bänken (Titelbild in Bank 2) erzeugen.
RUN git clone --depth 1 https://github.com/sverx/devkitSMS /opt/devkitSMS \
 && gcc -O2 -o /usr/local/bin/ihx2sms "$(find /opt/devkitSMS -name ihx2sms.c | head -1)" \
 && gcc -O2 -o /usr/local/bin/makesms /opt/devkitSMS/tools/makesms/src/makesms.c

ENV DEVKITSMS=/opt/devkitSMS
WORKDIR /work
