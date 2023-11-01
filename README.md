# mkdocs-git-committers-plugin-2

MkDocs plugin for displaying a list of committers associated with a file in
mkdocs. The plugin uses [GitHub's GraphQL
API](https://docs.github.com/en/graphql) to fetch the list of contributors for
each page.

Other MkDocs plugins that use information to fetch authors:

- [`mkdocs-git-authors-plugin`](https://github.com/timvink/mkdocs-git-authors-plugin) for displaying user names a number of lines contributed (uses local Git information)
- [`mkdocs-git-committers-plugin`](https://github.com/byrnereese/mkdocs-git-committers-plugin) display contributors for a page (uses local Git information, completed with REST GitHub API v3)

## History

This is a fork from the original [`mkdocs-git-committers-plugin`](https://github.com/byrnereese/mkdocs-git-committers-plugin) by @byrnereese.

I had to create this fork so that it could be uploaded and distributed through PyPi. The package has been renamed to `mkdocs-git-committers-plugin-2`.

This "v2" differs from the original by:

- Fetch contributors directly from GitHub
- Eliminate the need to match git commit logs with entries in GitHub, and thus GitHub API calls
- No more risk of matching the incorrect contributor as the information comes directly from GitHub
- last_commit_date is now populated with local git info
- Use a cache file to speed up following builds: authors are fetched from GitHub for a page only if that page has changed since the last build

All of the above improves accuracy and performances.

Note: the plugin configuration in `mkdocs.yml` still uses the original `git-committers` sections.

## material for mkdocs theme

This plugin is integrated in the [material for mkdocs](https://squidfunk.github.io/mkdocs-material/) theme by [Martin Donath](https://github.com/squidfunk).

## Limitations

- Getting the contributors relies on what is available on GitHub. This means that for new files, the build will report no contributors (and informed you with a 404 error which can be ignored)  
  When the file is merged, the contributors will be added normally.
- For now, Git submodule is not supported and will report no contributors.

## Setup

Install the plugin using pip:

`pip install mkdocs-git-committers-plugin-2`

Activate the plugin in `mkdocs.yml`:

```yaml
plugins:
  - git-committers:
      repository: organization/repository
      branch: main
      token: !ENV ["MKDOCS_GIT_COMMITTERS_APIKEY"]
```

If the token is not set in `mkdocs.yml` it will be read from the `MKDOCS_GIT_COMMITTERS_APIKEY` environment variable.

**Change in 2.0.0: if no token is present, the plugin will NOT add provide git committers.**

> **Note:** If you have no `plugins` entry in your config file yet, you'll likely also want to add the `search` plugin. MkDocs enables it by default if there is no `plugins` entry set, but now you have to enable it explicitly.

More information about plugins in the [MkDocs documentation][mkdocs-plugins].

## Config

- `enabled` - Disables plugin if set to `False` for e.g. local builds (default: `True`)
- `repository` - The name of the repository, e.g. 'ojacques/mkdocs-git-committers-plugin-2'
- `branch` - The name of the branch to get contributors from. Example: 'master' (default)
- `token` - A github fine-grained token for GitHub GraphQL API calls (classic tokens work too). The token does not need any scope: uncheck everything when creating the GitHub Token at [github.com/settings/personal-access-tokens/new](https://github.com/settings/personal-access-tokens/new), unless you access private repositories.
- `enterprise_hostname` - For GitHub enterprise: the enterprise hostname.
- `docs_path` - the path to the documentation folder. Defaults to `docs`.
- `cache_dir` - The path which holds the authors cache file to speed up documentation builds. Defaults to `.cache/plugin/git-committers/`. The cache file is named `page-authors.json.json`.
- `exclude` - Specify a list of page source paths (one per line) that should not have author(s) or last commit date included (excluded from processing by this plugin). Default is empty. [Example Usage](https://timvink.github.io/mkdocs-git-authors-plugin/options.html#exclude).

## Usage

### Display Last Commit

In addition to displaying a list of committers for a file, you can also access
the last commit date for a page if you want to display the date the file was
last updated.

#### Template Code for last commit

```django hljs
<ul class="metadata page-metadata" data-bi-name="page info" lang="en-us" dir="ltr">
  <li class="last-updated-holder displayDate loading">
    <span class="last-updated-text">Last updated:</span>
    <time role="presentation" datetime="2018-10-25T00:00:00.000Z" data-article-date-source="ms.date">{% if last_commit_date %}{{ last_commit_date }}{% endif %}</time>
  </li>
</ul>
```

### Display List of Committers

#### Avatar

The avatar of the contributors is provided by GitHub. It uses maximal resolution.

#### Template Code for avatars

```django hljs
{% block footer %}
<ul class="metadata page-metadata" data-bi-name="page info" lang="en-us" dir="ltr">
  <li class="contributors-holder">
    <span class="contributors-text">Contributors</span>
    <ul class="contributors" data-bi-name="contributors">
      {%- for user in committers -%}
      <li><a href="{{ user.url }}" title="{{ user.name }}" data-bi-name="contributorprofile" target="_blank"><img src="{{ user.avatar }}" alt="{{ user.name }}"></a></li>
      {%- endfor -%}
    </ul>
  </li>
</ul>
{% endblock %}
```

#### CSS

```css
.metadata{
    list-style:none;
    padding:0;
    margin:0;
    margin-bottom: 15px;
    color: #999;
    font-size:0.85em;
}
.metadata.page-metadata .contributors-text{
    margin-right:5px
}
body[dir=rtl] .metadata.page-metadata .contributors-text{
    margin-right:0;
    margin-left:5px
}
.page-metadata .contributors{
    display:inline-block;
    list-style:none;
    margin:0!important;
    padding:0!important
}
.page-metadata .contributors li{
    display:inline-block;
    vertical-align:top;
    margin:0;
    padding:0
}
```

#### Javascript

```javascript
    $( '.contributors img[data-src]' ).each( function() {
        src = $(this).attr("data-src");
        $(this).attr('src',src);
    });
```

More information about templates [here][mkdocs-template].

More information about blocks [here][mkdocs-block].

[mkdocs-plugins]: http://www.mkdocs.org/user-guide/plugins/
[mkdocs-template]: https://www.mkdocs.org/user-guide/custom-themes/#template-variables
[mkdocs-block]: https://www.mkdocs.org/user-guide/styling-your-docs/#overriding-template-blocks

## Acknowledgements

Thank you to the following contributors:

- Byrne Reese - original author, maintainer
- Nathan Hernandez
- Chris Northwood
- Martin Donath
