import { spawn } from "node:child_process";
import { resolve } from "node:path";
import { Plugin } from "@opencode/plugin";

export default Plugin.define({
  id: "sloperator.run-slop",
  setup: async (ctx) => {
    await ctx.tool.transform((tools) => {
      tools.add({
        name: "run_slop",
        description:
          "Run a SlopLang file with sloperator. Paths are absolute or relative to the project root. Returns JSON with stdout, stderr, and exitCode.",
        input: {
          type: "object",
          properties: {
            path: { type: "string", description: "Path to the .slop file to run" },
          },
          required: ["path"],
          additionalProperties: false,
        },
        options: { codemode: false },
        execute: async (input, context) => {
          const { path } = input as { path: string };
          const root = ctx.location.project.directory;
          const result = await new Promise<{
            stdout: string;
            stderr: string;
            exitCode: number | null;
          }>((resolveResult, reject) => {
            const child = spawn(
              "uv",
              ["run", "--no-active", "sloperator.py", resolve(root, path)],
              { cwd: root, signal: context.signal, stdio: ["ignore", "pipe", "pipe"] },
            );
            let stdout = "";
            let stderr = "";
            child.stdout.setEncoding("utf8");
            child.stderr.setEncoding("utf8");
            child.stdout.on("data", (chunk: string) => {
              stdout += chunk;
            });
            child.stderr.on("data", (chunk: string) => {
              stderr += chunk;
            });
            child.on("error", reject);
            child.on("close", (exitCode) => {
              resolveResult({ stdout, stderr, exitCode });
            });
          });
          return { content: JSON.stringify(result) };
        },
      });
    });
  },
});
