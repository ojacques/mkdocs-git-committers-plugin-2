# mkdocs-git-committers-plugin

MkDocs plugin for displaying a list of committers associated with a file in mkdocs.

## Setup

Install the plugin using pip:

`pip install mkdocs-git-committers-plugin`

Activate the plugin in `mkdocs.yml`:
```yaml
plugins:
  - search
  - git-committers
```

> **Note:** If you have no `plugins` entry in your config file yet, you'll likely also want to add the `search` plugin. MkDocs enables it by default if there is no `plugins` entry set, but now you have to enable it explicitly.

More information about plugins in the [MkDocs documentation][mkdocs-plugins].

## Config

* `enterprise_hostname` - The enterprise hostname of your github account (Github Enterprise customers only).
* `repository` - The name of the repository, e.g. 'byrnereese/mkdocs-git-committers-plugin'
* `branch` - The name of the branch to pull commits from, e.g. 'master' (default)
* `token` - A github Personal Access Token to avoid github rate limits

Tip: You can specify the GitHub token via an environment variable in the following way:

```yaml
plugins:
  - git-committers:
      repository: johndoe/my-docs
      branch: master
      token: !!python/object/apply:os.getenv ["MKDOCS_GIT_COMMITTERS_APIKEY"]
```

If the token is not set in `mkdocs.yml` it will be read from the `MKDOCS_GIT_COMMITTERS_APIKEY` environment variable.

**If no token is present, the plugin will determine information with local git repository information only.**

## Usage

### Display Last Commit

In addition to displaying a list of committers for a file, you can also access
the last commit date for a page if you want to display the date the file was
last updated.

#### Template Code

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

If the GitHub token is configured, a GitHub API request is made to retrieve the
avatar from GitHub. If not, the avatar attribute is populated with gravatar
identicon with an MD5 hash on the email address. If the author has configured
gravatar for this email address, the avatar will show properly, otherwise a
random but fixed gravatar identicon is generated.

#### Template Code

```django hljs
{% block footer %}
<ul class="metadata page-metadata" data-bi-name="page info" lang="en-us" dir="ltr">
  <li class="contributors-holder">
    <span class="contributors-text">Contributors</span>
    <ul class="contributors" data-bi-name="contributors">
      {%- for user in committers -%}
      <li><a href="{{ user.repos }}" title="{{ user.name }}" data-bi-name="contributorprofile"><img src="../img/contributor.svg" data-src="{{ user.avatar }}" alt="{{ user.name }}"></a></li>
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

* Nathan Hernandez
* Chris Northwood