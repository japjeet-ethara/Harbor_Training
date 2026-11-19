FROM golang:1.23
RUN curl -LsSf https://astral.sh/uv/0.9.7/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"
RUN uv tool install --python 3.12 "harbor-rewardkit==0.2.4"
COPY . /tests/
