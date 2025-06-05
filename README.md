# mkdocs-git-committers-plugin-2

MkDocs plugin for displaying a list of committers associated with a file in
mkdocs. The plugin uses GitHub or GitLab API to fetch the list of contributors
for each page.

🥳 NEW! Works with GitLab too!

For ease of use, this plugin is integrated in the [material for
mkdocs](https://squidfunk.github.io/mkdocs-material/) theme by [Martin
Donath](https://github.com/squidfunk). See [Mkdocs material
documentation](https://squidfunk.github.io/mkdocs-material/setup/adding-a-git-repository/#document-contributors).

Other MkDocs plugins that use information to fetch authors:

- [`mkdocs-git-authors-plugin`](https://github.com/timvink/mkdocs-git-authors-plugin) for displaying user names a number of lines contributed (uses local Git information)
- [`mkdocs-git-committers-plugin`](https://github.com/byrnereese/mkdocs-git-committers-plugin) display contributors for a page (uses local Git information, completed with REST GitHub API v3)

## Setup

Install the plugin using pip:

`pip install mkdocs-git-committers-plugin-2`

Activate the plugin in `mkdocs.yml`:

For a repository hosted on GitHub:

```yaml
plugins:
  - git-committers:
      repository: organization/repository
```

For a repository hosted on GitLab:

```yaml
plugins:
  - git-committers:
      gitlab_repository: 12345678
      token: !ENV ["CI_JOB_TOKEN"]
```

For a repository hosted on GitLab, you need to provide a token so that the
plugin can access the GitLab API. If the token is not set in `mkdocs.yml` it
will be read from the `MKDOCS_GIT_COMMITTERS_APIKEY` environment variable.

For a repository hosted on GitHub, you can provide a token to increase the rate
limit and go beyond the default 60 requests per hour per IP address. The plugin
will make one request per mkdocs document. The token does not need any scope:
uncheck everything when creating the GitHub Token at
[github.com/settings/personal-access-tokens/new](https://github.com/settings/personal-access-tokens/new),
unless you access private repositories.

For private GitHub repositories, you only need to allow read-only access to `Contents` and `Metadata` on the target repository. This could be done by setting `Read-only` access of `Permissions > Repository permissions > Contents`.

## Counting Contributors

* In GitHub repositories, the commit authors, [committers](https://stackoverflow.com/a/18754896), and [co-authors](https://docs.github.com/en/pull-requests/committing-changes-to-your-project/creating-and-editing-commits/creating-a-commit-with-multiple-authors) are counted as contributors. However, the plugin requires a GitHub token to fetch the list of co-authors. If co-authors exist but no token is provided, the plugin will show a warning and will only display the commit authors and committers.
* In GitLab repositories, only the commit authors are counted as contributors.

## Config

- `enabled` - Disables plugin if set to `False` for e.g. local builds (default: `True`)
- `repository` - For GitHub, the name of the repository, e.g.
  'ojacques/mkdocs-git-committers-plugin-2'
- `gitlab_repository` - For GitLab, the project ID, e.g. '12345678'
- `branch` - The name of the branch to get contributors from. Example: 'master'
  (default)
- `token` - A GitHub or GitLab personal access token for REST API calls. 
  - For GitHub, token does not need any scope: uncheck everything when creating
    the GitHub Token at
    [github.com/settings/personal-access-tokens/new](https://github.com/settings/personal-access-tokens/new),
    unless you access private repositories.
  - For GitLab, a
    [project access token](https://docs.gitlab.com/ee/user/project/settings/project_access_tokens.html)
    scoped to `read_api` is expected to work. That way, the token is limited to
    the project and has access to read the repository. You could use a personal
    access token at
    [gitlab.com/-/profile/personal_access_tokens](https://gitlab.com/-/profile/personal_access_tokens),
    but it will grant access to more repositories than you want.
- `enterprise_hostname` - For GitHub enterprise: the GitHub enterprise hostname.
- `gitlab_hostname` - For GitLab: the GitLab hostname if different from 
  gitlab.com (self-hosted).
- `api_version` - For GitHub and GitLab self-hosted, the API version part that needs to be appended to the URL. 
  Defaults to v4 for GitLab, and nothing for GitHub Enterprise (you may need `v3`).
- `docs_path` - the path to the documentation folder. Defaults to `docs/`.
- `cache_dir` - The path which holds the authors cache file to speed up
  documentation builds. Defaults to `.cache/plugin/git-committers/`. The cache
  file is named `page-authors.json`.
- `exclude` - Specify a list of page source paths (one per line) that should not
  have author(s) or last commit date included (excluded from processing by this
  plugin). Default is empty. Examples:

  ```
  # mkdocs.yml
  plugins:
    - git-committers:
        repository: organization/repository
        exclude:
          - README.md
          - subfolder/page.md
          - another_page.md
          - all_files_inside_folder/*
          - folder_and_subfolders/**
  ```
- `exclude_committers` - Specify a list of usernames to exclude certain committers. Default is empty.

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

## Limitations

- Getting the contributors relies on what is available on GitHub or GitLab.
- For now, non-recursive Git submodule is supported for GitHub, while GitLab submodules and recursive submodules will report no contributors.
- GitLab users may not be properly identified. See [issue #50](https://github.com/ojacques/mkdocs-git-committers-plugin-2/issues/50)

## Usage

You have 2 options to use this plugin:

1. Use Mkdocs material theme (see [Mkdocs material
documentation](https://squidfunk.github.io/mkdocs-material/setup/adding-a-git-repository/#document-contributors)).
1. Use the plugin directly in your template. See below.

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
- PTKay
- Guts
- Fir121
- dstockhammer
- thor
- n2N8Z
- barreeeiroo
- j3soon
- vrenjith
- rkorzeniec
- karelbemelmans
- andrew-rowson-lseg
