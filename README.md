# discordimageindex
Used in https://github.com/toasterofbread/spmp

<br/>

### Currently hosted as a [Supabase](https://supabase.com/) edge function

The Supabase URL and api key can be found here: https://github.com/toasterofbread/spmp/blob/main/keys.properties

<br/>

**To directly view the source code of the hosted function (get-images):**

- Send a get request to "https://api.supabase.com/v1/projects/opdupqbpxdfaqgdffyun/functions/get-images/body" with the "Authorization" header set to "Bearer: <api key>"
- Decode Brotli-encoded response

As a curl command:
```
curl 'https://api.supabase.com/v1/projects/opdupqbpxdfaqgdffyun/functions/get-images/body' -H "Authorization: Bearer <api key>" --output - | brotli -d -o source_code.js
```
