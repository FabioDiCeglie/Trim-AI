/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}", "./src/**/*.css"],
  theme: {
    extend: {
      colors: {
        trim: {
          green: "#1DB954",
          "green-hover": "#1ed760",
          base: "#121212",
          elevated: "#181818",
          card: "#282828",
          muted: "#b3b3b3",
        },
      },
    },
  },
  plugins: [],
};
