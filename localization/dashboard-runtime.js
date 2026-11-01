'use strict';
// Explicit preference only: a new session always starts in English.
const NodeLiftI18n = (() => {
  const normalize = value => ['en', 'zh-Hans', 'it'].includes(value) ? value : 'en';
  let language = 'en';
  try { language = normalize(localStorage.getItem('nodelift-language')); } catch (_) {}
  const t = (key, ...args) => {
    key = Object.hasOwn(NodeLiftLegacy,key) ? NodeLiftLegacy[key] : key;
    const catalog = NodeLiftCatalogs[language];
    const template = catalog && Object.hasOwn(catalog, key) ? catalog[key] : key;
    return String(template).replace(/\{(\d+)\}/g, (match, i) => i < args.length ? String(args[i]) : match);
  };
  function apply() {
    document.documentElement.lang = language;
    document.querySelectorAll('[data-i18n]').forEach(node => { node.textContent = t(node.dataset.i18n); });
    for (const attr of ['placeholder', 'aria-label', 'alt']) {
      document.querySelectorAll('[data-i18n-'+attr+']').forEach(node => node.setAttribute(attr, t(node.getAttribute('data-i18n-'+attr))));
    }
    const picker = document.getElementById('language');
    if (picker) picker.value = language;
  }
  function setLanguage(value) {
    language = normalize(value);
    try { localStorage.setItem('nodelift-language', language); } catch (_) {}
    apply();
    document.dispatchEvent(new Event('nodelift-languagechange'));
  }
  return { t, apply, setLanguage, get language() { return language; }, get locale() { return {en:'en-US', 'zh-Hans':'zh-CN', it:'it-IT'}[language]; } };
})();
NodeLiftI18n.apply();
