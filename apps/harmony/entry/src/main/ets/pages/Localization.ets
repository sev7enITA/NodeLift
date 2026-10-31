import { chineseMessages } from './ChineseMessages';

export function translate(key: string, language: string): string {
  return language === 'zh-Hans' ? (chineseMessages[key] ?? key) : key;
}
