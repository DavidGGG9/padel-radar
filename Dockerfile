FROM python:3.12.8-slim

#Do not use env as this would persist after the build and would impact your containers, children images
ARG DEBIAN_FRONTEND=noninteractive

# force the stdout and stderr streams to be unbuffered.
ENV PYTHONUNBUFFERED=1

RUN apt-get -y update \
  && apt-get -y upgrade \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/* \
  && useradd --uid 10000 -ms /bin/bash runner

WORKDIR /home/padel-chatbot/

ENV PATH="${PATH}:/home/padel-chatbot/.local/bin"

COPY pyproject.toml ./
COPY functions ./functions
COPY collections ./collections
COPY app ./app

RUN pip install --upgrade pip \
  && pip install --no-cache-dir poetry \
  && poetry config virtualenvs.in-project true \
  && poetry install --only main --no-root

USER 10000

EXPOSE 8000

ENTRYPOINT [ "poetry", "run" ]

# To run locally
CMD [ "sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000" ]
# To run on cloud run
# CMD [ "sh", "-c", "uvicorn twitter_api.main:app --host 0.0.0.0 --port $PORT" ]
# $CHA_END