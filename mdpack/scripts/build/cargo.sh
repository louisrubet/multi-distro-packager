#!/bin/bash
# Builds a Rust project with cargo, with a toolchain from rustup (the distros' are often too old
# for recent editions), kept in /cache with the crates and the build; then installs the binaries
# (APP_BUILD_CARGO_BINS, the package name by default) in /usr/bin and the other files
# (APP_BUILD_FILES, as source:destination) in /app/install.
set -e
source /app/env.sh
export RUSTUP_HOME=/cache/rustup CARGO_HOME=/cache/cargo
export CARGO_TARGET_DIR=/cache/target/${PKG_PACKAGE}
export PATH=${CARGO_HOME}/bin:${PATH}
toolchain=${APP_BUILD_RUST_VERSION:-stable}
if [ ! -x ${CARGO_HOME}/bin/rustup ]; then
    curl -sSf https://sh.rustup.rs | sh -s -- -y --no-modify-path --profile minimal --default-toolchain none
fi
rustup toolchain install ${toolchain} --profile minimal
rustup default ${toolchain}

cd /app/src
cargo build --release ${APP_BUILD_CARGO_OPTIONS}

mkdir -p /app/install
for bin in ${APP_BUILD_CARGO_BINS:-${PKG_PACKAGE}}; do
    install -Dm755 ${CARGO_TARGET_DIR}/release/${bin} /app/install/usr/bin/${bin}
done
for file in ${APP_BUILD_FILES}; do
    install -Dm644 "${file%%:*}" "/app/install${file#*:}"
done
