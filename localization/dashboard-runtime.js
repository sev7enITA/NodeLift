'use strict';
// Explicit preference only: a new session always starts in English.
const NodeLiftI18n = (() => {
  let language = 'en';
  try { if (localStorage.getItem('nodelift-language') === 'zh-Hans') language = 'zh-Hans'; } catch (_) {}
  const t = (key, ...args) => {
    key = Object.hasOwn(NodeLiftLegacy,key) ? NodeLiftLegacy[key] : key;
    const template = language === 'zh-Hans' && Object.hasOwn(NodeLiftChinese, key) ? NodeLiftChinese[key] : key;
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
    language = value === 'zh-Hans' ? 'zh-Hans' : 'en';
    try { localStorage.setItem('nodelift-language', language); } catch (_) {}
    apply();
    document.dispatchEvent(new Event('nodelift-languagechange'));
  }
  return { t, apply, setLanguage, get language() { return language; }, get locale() { return language === 'zh-Hans' ? 'zh-CN' : 'en-US'; } };
})();
NodeLiftI18n.apply();
