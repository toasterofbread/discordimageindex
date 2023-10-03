import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const DISCORD_WEBHOOK_URL = Deno.env.get("DISCORD_WEBHOOK_URL")!
const SUPABASE_URL = Deno.env.get("SUPABASE_URL")
const SUPABASE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!

async function downloadImage(image_url: string): Promise<Blob | null> {
  try {
    const response = await fetch(image_url)

    if (!response.ok) {
      throw new Error(`Fetching image from ${image_url} failed. Status: ${response.status}`)
    }

    const buffer = await response.arrayBuffer()
    return new Blob([buffer], { type: "image/jpeg" })
  } 
  catch (error) {
    console.error(`Error fetching image from ${image_url}: ${error}`)
    return null
  }
}

async function onImageAdded(supabase, image_id: string, image_url: string) {
  await supabase
    .from("images")
    .insert({ id: image_id, attachment_url: image_url })
}

interface ItemType {
  item_ids: string[],
  getImageUrl: (url: string) => Promise<string | null>,
  results: (string | null)[]
}

serve(async (req) => {
  
  /*
    Input format:
    {
      "images": [
        { "id": "SONG_ID", "image_url": "IMAGE_URL" }
      ]
    }
  */
  const images: any[] = (await req.json()).images

  const supabase = createClient(SUPABASE_URL, SUPABASE_KEY)
  
  const image_results: (string | null)[] = []
  
  const image_ids: string[] = images.map((item) => {
    return item.id
  })
  const existing_images: Record<string, string> = (
      await supabase
      .from("images")
      .select()
      .filter("id", "in", `(${image_ids.join(",")})`)
    )
    .data
    .reduce((map, obj) => {
      map[obj.id] = obj.attachment_url
      return map
    }, {})

  for (const { id, image_url } of images) {
    const existing_url = existing_images[id]
    if (existing_url !== undefined) {
      image_results.push(existing_url)
      continue
    }

    if (image_url == null) {
      image_results.push(null)
      continue
    }
    
    const image_data = await downloadImage(image_url)
    if (image_data == null) {
      image_results.push(null)
      continue
    }

    const form_data = new FormData()
    
    form_data.append("payload_json", JSON.stringify({
      content: id
    }))

    let image_name = image_url.split("/").pop()?.split("?")[0]
    if (image_name?.includes(".") != true) {
      image_name = "image.png"
    }
    
    console.log(`Uploading image with name: ${image_name} (from ${image_url})`)
    form_data.append("file1", image_data, image_name)
    
    const response = await fetch(DISCORD_WEBHOOK_URL, {
      method: "POST",
      body: form_data,
    })
    
    const { attachments } = await response.json()
    const attachment_url = attachments[0].url
    
    image_results.push(attachment_url)
    onImageAdded(supabase, id, attachment_url)
  }

  console.log(
    `OUTPUT: ${JSON.stringify({
      attachment_urls: image_results
    })}`
  )

  return new Response(
    JSON.stringify({
      attachment_urls: image_results
    }),
    { headers: { "Content-Type": "application/json" } },
  )
})
