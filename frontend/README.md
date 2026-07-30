
  # Climate-based Navigation App

  This is a code bundle for Climate-based Navigation App. The original project is available at https://www.figma.com/design/MvemBSy8sGGAYZr9hq5Jth/Climate-based-Navigation-App.

  ## Backend / preset notes

  - The backend now keeps the original Heat Score weights in `data/presets.json`.
  - The new preset workflow uses `data/preset_catalog.json`, `data/route_tags.json`, and `data/preset_output_schema.json`.
  - The intended flow is `STT -> GPT preset extraction -> user confirmation/edit -> tag-based route recommendation`.

  ## Running the code

  Run `npm i` to install the dependencies.

  Run `npm run dev` to start the development server.
  