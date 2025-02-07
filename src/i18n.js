import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

const resources = {
    en: {
        translation: {
            register: "Register",
            login: "Login",
            devices: "Devices",
            welcome: "Welcome to the Lab Management App",
            username: "Username",
            password: "Password",
            submit: "Submit",
        },
    },
    zh: {
        translation: {
            register: "注册",
            login: "登录",
            devices: "设备管理",
            welcome: "欢迎来到实验室管理系统",
            username: "用户名",
            password: "密码",
            submit: "提交",
        },
    },
};

i18n.use(initReactI18next).init({
    resources,
    lng: "en", // 默认语言
    interpolation: {
        escapeValue: false,
    },
});

export default i18n;
