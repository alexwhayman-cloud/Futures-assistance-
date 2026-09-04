# Markdown snippets

Copy-paste blocks for READMEs, docs sites and GitHub. Paths assume the file lives at the repo root; adjust `branding/` if not.

## README header (light and dark aware)

```html
<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="branding/logo/svg/twocoasts-logo-primary-reverse-tagline.svg">
    <img alt="TwoCoasts" src="branding/logo/svg/twocoasts-logo-primary-tagline.svg" width="420">
  </picture>
</p>
<h3 align="center">One-line description of the project</h3>
```

## Mark only (for sub-project READMEs)

```html
<img src="branding/logo/svg/twocoasts-mark-day.svg" alt="TwoCoasts" width="64" align="left">
```

## Badge

```markdown
[![TwoCoasts project](https://img.shields.io/badge/TwoCoasts-Dubai%20%C2%B7%20Thailand-0FA3B1?labelColor=0B2545&style=flat-square)](#)
```

## Section divider

```markdown
<img src="branding/logo/svg/twocoasts-wordmark-mono-navy.svg" alt="" width="120">

---
```

## Footer

```markdown
---
<p align="center"><sub>A <b>TwoCoasts</b> project · Dubai · Thailand</sub></p>
```

## Docs sites (MkDocs Material)

```yaml
theme:
  name: material
  logo: branding/logo/svg/twocoasts-mark-day.svg
  favicon: branding/logo/favicon/favicon.svg
  font:
    text: Inter
    code: JetBrains Mono
  palette:
    - scheme: default
      primary: custom
extra_css:
  - branding/tokens/twocoasts.css
```

## Docusaurus

```js
// docusaurus.config.js
themeConfig: {
  navbar: {
    logo: { alt: 'TwoCoasts', src: 'branding/logo/svg/twocoasts-logo-primary.svg', srcDark: 'branding/logo/svg/twocoasts-logo-primary-reverse.svg' },
  },
},
```
