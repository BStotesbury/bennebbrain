module.exports = {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],

  theme: {
    extend: {
      colors: {
        lavender:  "#d8d4f2",
        cappuccino: "#846C5B",
        charcoal:  "#36454F",
        mauve:     "#E0B0FF",
      },
      fontFamily: {
        heading: ["Satoshi", "sans-serif"],
        sans:    ["Inter",   "sans-serif"],
      },
    },
  },
  plugins: [],
};