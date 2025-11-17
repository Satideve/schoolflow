/* C:\coding_projects\dev\schoolflow\frontend\postcss.config.cjs */
const tailwindPostcss = require('@tailwindcss/postcss');

module.exports = {
  plugins: [
    tailwindPostcss(),
    require('autoprefixer')(),
  ],
};
