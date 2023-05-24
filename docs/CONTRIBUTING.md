# Contributing to Oobabot

## How can you contribute?

Find an [issue from our GitHub page](https://github.com/chrisrude/oobabot-plugin/issues), and mention that you'd like to work on it.  Let me know if you need any help getting started, I'm happy to help!

If the one you want to work on isn't there, please open an issue first so we can discuss it.  I'm happy to accept any contributions, but things will go more smoothly if we're on the same page before a lot of work is put in.  I want to help you be successful!

Read the stuff below, and then read the [development environment](#development-environment) section.  If you have any questions, please ask.  For contributions, please follow the [coding guidelines](#coding-guidelines).

## Development Environment

tl;dr: Install Python 3.9+, [install poetry](https://python-poetry.org/docs/), clone the repo, run `poetry install`, run `poetry run oobabot`

```bash
sudo apt-get install python3 git curl

# install poetry (see https://python-poetry.org/docs/)
curl -sSL https://install.python-poetry.org | python3 -

# or whatever the poetry installer tells you to do
export PATH="~/.local/bin:$PATH"

# clone the repo and cd into it
git clone https://github.com/chrisrude/oobabot-plugin.git
cd oobabot

# create a conda environment and activate it
conda create --name (basename $PWD) python=3.10.9
conda activate oobabot-plugin

# this will build the project, downloading all dependencies
poetry install
```

You'll need a machine running Python 3.10.9 or higher, and [poetry](https://python-poetry.org/) installed.  Then just clone the repo.

Once you have the code checked out, you can install the dependencies with `poetry install`.  This will install all the dependencies, including the dev dependencies.

### Updating Dependencies

From time to time additional dependencies will be added.  You can easily update your local environment with `poetry install`.  This will update all dependencies, including dev dependencies.

## Coding Guidelines

The project is built to support Python 3.10.9 and higher.  It uses [poetry](https://python-poetry.org/) to build and package with.  It uses [black](https://github.com/psf/black) for code formatting, with assistance from isort and flake8.  It uses [pytest](https://docs.pytest.org/en/stable/) for testing.

A lot of the code is based on the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html).  I'm not religious about it, but I do try to follow it.  Generally, just try to match the style of whatever is already there.  Even if you would prefer different style choices, keeping things consistent is more important.  If you're not sure, ask!

## Submitting Your Pull Request

Before pushing, make sure you have pre-commit hooks enabled.  This will help you catch any simple issues before you push.  It will also automatically fix any formatting issues, so you don't have to micro that yourself.  You can install them with `poetry run pre-commit` as well as `poetry run pre-commit install`.

Once you've made your changes, you can submit a pull request.  I'll review it, and if everything looks good, I'll merge it in.  If there are any issues, I'll let you know and we can work through them together.

Thank you!
