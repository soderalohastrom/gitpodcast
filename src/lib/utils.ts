import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}


// WebVTT Parser
export function parseWebVTT(vtt: string) {
    vtt = vtt.replace(/<em>/gi, "").replace(/<\/em>/gi, "")
    console.log(vtt);
    console.log("Herereee");
    const lines = vtt.split("\n");
    const regex = /(\d{2}):(\d{2}):(\d{2})\.(\d{3})/;

    const subtitles: { start: number; end: number; text: string; }[] = [];
    let currentSubtitle = { start: 0, end: 0, text: "" };
    let isStyle = false;

    lines.forEach((line) => {
        // line = line;
        // Skip sequence numbers
        if (/^\d+$/.test(line)) return

        if (line === "STYLE" || line.startsWith("::cue")) {
            isStyle = true;
        }

        if (isStyle) {
            if (line === "" || line === "}") {
                isStyle = false;
            }
            return; // Skip style blocks
        }

        const match = regex.exec(line);
        if (match) {
            const times = line.split(" --> ");
            if (!times || times.length !== 2) return;

            const startSeconds = parseTime(times[0] ?? '0');
            const endSeconds = parseTime(times[1]?.split(' ')[0] ?? '0');

            currentSubtitle.start = startSeconds;
            currentSubtitle.end = endSeconds;
        } else if (line === "") {
            if (currentSubtitle.text) {
                // currentSubtitle.text = currentSubtitle.text.trim();
                subtitles.push({ ...currentSubtitle });
                currentSubtitle = { start: 0, end: 0, text: "" };
            }
        } else {
            currentSubtitle.text += `${line}\n`;
        }
    });

    return subtitles;
}



  export function parseTime(time: string): number {
    const parts = time.split(":").map(Number);

    // Validate that we have exactly three parts: hrs, min, and secMs
    if (parts.length < 2 || parts.length > 3 || parts.some(isNaN)) {
      throw new Error("Invalid time format");
    }

    const [hrs = 0, min = 0, secMs = 0] = parts; // Provide a default value of 0 for secMs

    // Now, secMs is guaranteed to be defined, so you can safely use it
    const secMsString = secMs.toFixed(3); // Ensure it's treated as a fixed-point notation
    const [secString = '0', msString = '0'] = secMsString.split(".");

    const sec = parseFloat(secString) || 0;
    const ms = parseFloat(msString) || 0;

    return hrs * 3600 + min * 60 + sec + ms / 1000;
  }

  export function syncSubtitle(subtitles: string | any[], time: number | undefined) {
    // Find the current subtitle based on the video time
    for (let i = 0; i < subtitles.length; i++) {
      if ((time ?? 0) >= subtitles[i].start && (time ?? 0) < subtitles[i].end) {
        return i;
      }
    }
    return null;
  }