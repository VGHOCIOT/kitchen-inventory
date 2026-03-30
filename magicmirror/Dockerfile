FROM karsten13/magicmirror:latest

# Copy module source and install dependencies as part of the image build.
# This avoids runtime npm install into a bind-mounted directory (permission issues
# on Unraid where the host directory is owned by root but the container runs as node).
COPY --chown=node:node MMM-KitchenInventory /opt/magic_mirror/modules/MMM-KitchenInventory
RUN cd /opt/magic_mirror/modules/MMM-KitchenInventory && npm install --omit=dev
