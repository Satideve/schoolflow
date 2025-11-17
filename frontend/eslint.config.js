/* C:\coding_projects\dev\schoolflow\frontend\eslint.config.js */
export default [
  {
    files: ["**/*.{ts,tsx}"],
    languageOptions: {
      parserOptions: {
        ecmaVersion: "latest",
        sourceType: "module"
      }
    },
    rules: {
      "no-unused-vars": "warn",
      "no-undef": "error",
    },
  },
];
