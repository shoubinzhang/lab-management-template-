import i18n from 'i18next';
import { I18nextProvider } from 'react-i18next';

i18n.init({
  resources: {
    en: { translation: { "hello": "Hello, world!" } },
    fr: { translation: { "hello": "Bonjour, le monde!" } }
  },
  lng: 'en',
  fallbackLng: 'en',
  interpolation: { escapeValue: false }
});

const App = () => (
  <I18nextProvider i18n={i18n}>
    <div>{i18n.t('hello')}</div>
  </I18nextProvider>
);

export default App;
