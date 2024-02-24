import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { createBot, startBot, getMessage, sendMessage } from "https://deno.land/x/discordeno@18.0.1/mod.ts";

const DISCORD_BOT_TOKEN: string = Deno.env.get("DISCORD_BOT_TOKEN")!
const DISCORD_CHANNEL_ID: string = Deno.env.get("DISCORD_CHANNEL_ID")!
const SUPABASE_URL: string = Deno.env.get("SUPABASE_URL")
const SUPABASE_KEY: string = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!

/*
Input format:
{
	"images": [
		{ "id": "SONG_ID", "image_url": "IMAGE_URL" }
	]
}
*/
serve(async (req) => {
	const supabase = createClient(SUPABASE_URL, SUPABASE_KEY)
	const bot = await createDiscordBot()

	const images: any[] = (await req.json()).images
	const image_results: (string | null)[] = []

	const image_ids: string[] = images.map((item) => {
		return item.id
	})

	const image_messages =
		await supabase
			.from("image-messages")
			.select()
			.filter("id", "in", `(${image_ids.join(",")})`)

	const image_index: Record<string, string> =
		image_messages
			.data
			.reduce(
				(map, obj) => {
					map[obj.id] = obj.message_id
					return map
				},
				{}
			)

	for (const { id, image_url } of images) {
		const indexed_message: string | undefined = image_index[id]
		if (indexed_message !== undefined) {
			const message_image_url: string | undefined = await getExistingImage(bot, indexed_message)
			if (message_image_url !== undefined) {
				image_results.push(message_image_url)
				continue
			}
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

		let image_name: string = image_url.split("/").pop()?.split("?")[0]
		if (image_name?.includes(".") != true) {
			image_name = "image.png"
		}

		console.log(`Uploading image with name: ${image_name} (from ${image_url})`)

		const message = await sendMessage(
			bot,
			DISCORD_CHANNEL_ID,
			{
				content: id,
				file: {
					blob: image_data,
					name: image_name
				}
			}
		)

		const attachment_url: string = message.attachments[0].url
		image_results.push(attachment_url)

		onImageAdded(supabase, id, message.id.toString())
	}

	const output: string = JSON.stringify({attachment_urls: image_results})
	console.log(`OUTPUT: ${output}`)

	return new Response(output, { headers: { "Content-Type": "application/json" } })
})

async function createDiscordBot() {
	const bot = createBot({
		token: DISCORD_BOT_TOKEN
	})
	await startBot(bot)
	return bot
}

async function getExistingImage(bot, message_id: string): Promise<String | undefined> {
	const message = await getMessage(bot, DISCORD_CHANNEL_ID, message_id)
	return message.attachments[0].url
}

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

async function onImageAdded(supabase, image_id: string, message_id: string) {
	await supabase
		.from("image-messages")
		.insert({ id: image_id, message_id: message_id })
}
