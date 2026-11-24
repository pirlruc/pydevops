# syntax=docker/dockerfile:1
# Python quality image. Debian owns unsuffixed tags (glibc, consumer uv sync).
# No HEALTHCHECK. kics-scan disable=b03a748a-542d-44f4-bb86-9199ab4fd2d5
# Base tag in a comment for DOCKER-BUILD-003: dhi.io/python:3.13-debian13-dev

FROM dhi.io/node:24-debian13-dev@sha256:96e25a7d16cd1dff155387709b78bf6fc3d97fe229bd0ee776c569b7908a9b3f AS jscpd
WORKDIR /opt/jscpd
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts

FROM dhi.io/python:3.13-debian13-dev@sha256:7cf7dea69d646294bbb1c69239a544ac17bf8da851a16bedf43871901c9dcbc1 AS quality
COPY --from=dhi.io/uv:0-debian13@sha256:3003d7cdef643ab3a535dd4cfd29f56917750c378c1eb7c41fe20e30444e5bd2 \
  /uv /usr/local/bin/uv
COPY requirements.txt /tmp/requirements.txt
RUN /usr/local/bin/uv venv /opt/quality --python /usr/bin/python3 \
 && /usr/local/bin/uv pip install --python /opt/quality/bin/python --no-cache --require-hashes \
      -r /tmp/requirements.txt \
 && rm -f /tmp/requirements.txt

FROM dhi.io/python:3.13-debian13-dev@sha256:7cf7dea69d646294bbb1c69239a544ac17bf8da851a16bedf43871901c9dcbc1

LABEL org.opencontainers.image.title="ci-python" \
      org.opencontainers.image.description="Python quality toolchain: uv, quality CLIs, jscpd, syft, grype, cloc, jq. Debian 13. Non-root 1000:1000, linux/amd64." \
      org.opencontainers.image.source="https://github.com/pirlruc/pydevops" \
      org.opencontainers.image.vendor="pirlruc" \
      org.opencontainers.image.licenses="MIT"

ENV PATH="/opt/quality/bin:/opt/jscpd/node_modules/.bin:/usr/local/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      cloc=2.04-1 \
      jq=1.8.2-1+deb13u0+dhi1 \
      git=1:2.47.3-0+deb13u1+dhi2 \
      ca-certificates=20250419+deb13u1+dhi0 \
 && rm -rf /var/lib/apt/lists/* \
 && if ! id -u 1000 >/dev/null 2>&1; then \
      printf 'ci:x:1000:1000::/home/ci:/bin/sh\n' >> /etc/passwd; \
      printf 'ci:x:1000:\n' >> /etc/group; \
    fi \
 && mkdir -p /home/ci /workspace \
 && chown -R 1000:1000 /workspace /home/ci \
 && rm -rf /usr/lib/python3/dist-packages/pip \
      /usr/lib/python3/dist-packages/pip-*.dist-info \
      /usr/share/python-wheels/pip-*.whl \
      /usr/bin/pip /usr/bin/pip3

COPY --from=dhi.io/syft:1-debian13@sha256:592be9e9fb223f5bd3f175bba8f9191847b065cc97e03998cd3944c315b29128 \
  /usr/bin/syft /usr/local/bin/syft
COPY --from=dhi.io/grype:0-debian13@sha256:aa59b66b65c0cc54f094cd35614b203288477bc5d4d256be003b00a96a473925 \
  /usr/bin/grype /usr/local/bin/grype
COPY --from=dhi.io/node:24-debian13-dev@sha256:96e25a7d16cd1dff155387709b78bf6fc3d97fe229bd0ee776c569b7908a9b3f \
  /usr/bin/node /usr/local/bin/node
COPY --from=jscpd --chown=1000:1000 /opt/jscpd /opt/jscpd
COPY --from=quality --chown=1000:1000 /opt/quality /opt/quality

WORKDIR /workspace
RUN find / -xdev -type f \( -perm -4000 -o -perm -2000 \) -exec chmod a-s {} +
USER 1000:1000
ENTRYPOINT []
CMD ["sh"]
