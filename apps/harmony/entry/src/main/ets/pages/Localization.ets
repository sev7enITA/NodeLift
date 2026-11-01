import { chineseMessages } from './ChineseMessages';
import { italianMessages } from './ItalianMessages';

export function translate(key: string, language: string): string {
  if (language === 'zh-Hans') return chineseMessages[key] ?? key;
  if (language === 'it') return italianMessages[key] ?? key;
  return key;
}
