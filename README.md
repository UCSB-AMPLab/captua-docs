# Captua website

The source of <https://captua.org/>, the website and guides for Captua, built with Hugo Extended and Pagefind. English guides are published under `/docs/` and Spanish guides under `/guia/`. The Captua application itself is in [digitization-toolkit-software](https://github.com/UCSB-AMPLab/digitization-toolkit-software).

## Install and preview

Requires Node.js 22 or later. The checks also use Python 3, with no Python packages required.

```sh
npm ci
npm run build:preview
npm run preview
```

Open <http://127.0.0.1:4006/> for the English homepage, <http://127.0.0.1:4006/es/> for the Spanish homepage, and `/docs/` or `/guia/` for the guides. For review from another machine over Tailscale, run `HOST="$(tailscale ip -4)" npm run preview` and open port 4006 on that Tailscale address. Stop the preview server with Ctrl-C.

For live rebuilding while you edit content or layouts, run `npm run dev` after the first preview build. Pagefind indexes the generated HTML, so run `npm run build:preview` again before you check search results.

## Edit the site

- `content/en/` and `content/es/` hold the pages. An `_index.md` is a page that also has child pages.
- Each page sets its published address in `url` and its pairing with the other language in `translationKey`. Hugo produces the language links from `translationKey`.
- `data/docs_navigation.json` sets the guide sections, their order, and the interface labels. Page titles stay in each page's front matter; the navigation names pages by path.
- `data/site_copy.json` holds the homepage, header, and hub copy in both languages.
- `data/docs_media.json` holds the image path, size, alt text, and caption for each `media` shortcode.
- `data/translations_pending.json` lists the English pages that do not have a Spanish page yet. Remove a key from it when you add the Spanish page.
- `layouts/_partials/docs-shell.html` is the page shell for the guides and `home.html` is the homepage. Metadata is in `meta.html`.
- `layouts/_shortcodes/` holds the `callout` and `media` shortcodes.
- `static/` holds the stylesheet, browser script, fonts, logos, and images. The colours, the Mulish font, and the logos come from the Captua frontend.
- `migration/sources.json` records the source file in digitization-toolkit-software for each page moved from the earlier Quarto documentation.

Headings carry explicit IDs (`## Heading {#id}`). Keep them when you change a heading, so that existing links to a section still work.

### Shortcodes

```text
{{< callout type="warning" title="Optional title" appearance="simple" collapse="true" >}}
Markdown content.
{{< /callout >}}

{{< media id="key-in-data-docs_media" >}}
```

`type` is one of `note`, `tip`, `warning`, `caution`, or `important`. `appearance` and `collapse` are optional.

## Build and verify

```sh
npm run build
npm test
```

The production build writes `public/` and builds the search index. `npm test` checks the built site: internal links and fragments resolve, every image exists and has alt text, every page has one title and one H1 and is not empty, canonical addresses and the robots policy match the build, no URL carries a token or other credential, both language search indexes are present, the sitemap index covers both languages, and every English page with a `translationKey` has a Spanish page or is listed in `data/translations_pending.json`. Results are written to the ignored `reports/` directory.

The workflow in `.github/workflows/site.yml` builds and tests every pull request. On a push to `main`, after the checks pass, it deploys `public/` to Cloudflare Workers as static assets with Wrangler, using `wrangler.jsonc`, which also sets the custom domains `captua.org` and `www.captua.org`. Every page names `https://captua.org/` as its canonical address. The deploy reads two repository secrets, `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID`.

## Propose a change

Branch from `main`, open a pull request into `main`, and merge it once the `build` check passes. `main` is protected: it takes changes only through a pull request whose `build` check has passed on a branch that is up to date with `main`. Merging the pull request publishes the change to captua.org within a few minutes.
