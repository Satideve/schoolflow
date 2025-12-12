// C:\coding_projects\dev\schoolflow\frontend\tailwind.config.ts
import type { Config } from "tailwindcss";
import typography from "@tailwindcss/typography";

const config: Config = {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx,js,jsx,html}"],
  theme: {
    extend: {
      typography: (theme: any) => ({
        DEFAULT: {
          css: {
            color: theme("colors.slate.900"),
            a: {
              color: theme("colors.blue.600"),
              "&:hover": {
                color: theme("colors.blue.700"),
              },
            },
            code: {
              backgroundColor: theme("colors.slate.100"),
              padding: "0.125rem 0.25rem",
              borderRadius: theme("borderRadius.sm"),
            },
            "h1, h2, h3, h4": {
              color: theme("colors.slate.900"),
            },
          },
        },
        dark: {
          css: {
            color: theme("colors.slate.100"),
            a: {
              color: theme("colors.blue.400"),
              "&:hover": {
                color: theme("colors.blue.300"),
              },
            },
            code: {
              backgroundColor: theme("colors.slate.800"),
            },
            "h1, h2, h3, h4": {
              color: theme("colors.slate.100"),
            },
          },
        },
      }),
    },
  },
  plugins: [typography],
};

export default config;
