/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          700: "#991b1b",
          800: "#8B1D1D",
          900: "#6B1212",
        },
        leaf: {
          600: "#15803d",
          700: "#166534",
        },
      },
    },
  },
  plugins: [],
};
