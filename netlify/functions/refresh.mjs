/**
 * Netlify Function: Trigger GitHub Actions workflow for on-demand refresh.
 * Kaldes af refresh-knappen i webappen.
 */

export default async (req) => {
  // Kun POST-requests tilladt
  if (req.method !== "POST") {
    return new Response("Method not allowed", { status: 405 });
  }

  const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
  const GITHUB_REPO = process.env.GITHUB_REPO; // format: "username/ai-briefing"

  if (!GITHUB_TOKEN || !GITHUB_REPO) {
    console.error("Missing GITHUB_TOKEN or GITHUB_REPO environment variables");
    return new Response(JSON.stringify({ error: "Server configuration error" }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }

  try {
    // Trigger GitHub Actions via repository_dispatch
    const response = await fetch(
      `https://api.github.com/repos/${GITHUB_REPO}/dispatches`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${GITHUB_TOKEN}`,
          Accept: "application/vnd.github.v3+json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          event_type: "refresh-briefing",
        }),
      }
    );

    if (response.status === 204) {
      return new Response(
        JSON.stringify({ success: true, message: "Opdatering igangsat" }),
        {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }
      );
    } else {
      const errorText = await response.text();
      console.error(`GitHub API error: ${response.status} — ${errorText}`);
      return new Response(
        JSON.stringify({ error: "Kunne ikke starte opdatering" }),
        {
          status: 502,
          headers: { "Content-Type": "application/json" },
        }
      );
    }
  } catch (error) {
    console.error("Refresh function error:", error);
    return new Response(
      JSON.stringify({ error: "Internal server error" }),
      {
        status: 500,
        headers: { "Content-Type": "application/json" },
      }
    );
  }
};
