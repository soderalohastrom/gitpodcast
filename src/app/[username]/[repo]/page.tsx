"use client";

import { useParams } from "next/navigation";
import MainCard from "~/components/main-card";
import Loading from "~/components/loading";
import MermaidChart from "~/components/mermaid-diagram";
import { useDiagram } from "~/hooks/useDiagram";
import { ApiKeyDialog } from "~/components/api-key-dialog";
import { Button } from "~/components/ui/button";
import { ApiKeyButton } from "~/components/api-key-button";
import React, { useState } from 'react';

import WavesurferPlayer from '@wavesurfer/react'

export default function Repo() {
    const [wavesurfer, setWavesurfer] = useState(null)
    const [isPlaying, setIsPlaying] = useState(false)
    const onReady = (ws) => {
        setWavesurfer(ws)
        setIsPlaying(false)
    }
    const onPlayPause = () => {
        wavesurfer && wavesurfer.playPause()
    }

  const params = useParams<{ username: string; repo: string }>();
  const {
    diagram,
    error,
    loading,
    lastGenerated,
    cost,
    isRegenerating,
    showApiKeyDialog,
    tokenCount,
    handleModify,
    handleRegenerate,
    handleCopy,
    handleApiKeySubmit,
    handleCloseApiKeyDialog,
    handleOpenApiKeyDialog,
    handleAudio,
    audioUrl,
    audioRef
  } = useDiagram(params.username, params.repo);


  return (
    <div className="flex min-h-screen flex-col items-center p-4">
      <div className="flex w-full justify-center pt-8">
        <MainCard
          isHome={false}
          username={params.username}
          repo={params.repo}
          showCustomization={!loading && !error}
          onModify={handleModify}
          onRegenerate={handleRegenerate}
          onCopy={handleCopy}
          lastGenerated={lastGenerated}
        />
      </div>
      <div className="mt-8 flex w-full flex-col items-center gap-8">
        {loading ? (
          <div className="mt-12">
            <Loading cost={cost} isModifying={!isRegenerating} />
          </div>
        ) : error ? (
          <div className="mt-12 text-center">
            <p className="max-w-4xl text-lg font-medium text-red-600">
              {error}
            </p>
            {error.includes("Rate limit") && (
              <p className="mt-2 text-sm text-gray-600">
                Rate limits: 1 request per minute, 5 requests per day
              </p>
            )}
            {error.includes("token limit") && (
              <div className="mt-8 flex flex-col items-center gap-2">
                <ApiKeyButton onClick={handleOpenApiKeyDialog} />
                <p className="mt-2 text-sm">Your key will not be stored</p>
              </div>
            )}
          </div>
        ) : (
          <div className="flex w-full justify-center px-4">

              {/* <Button
                  onClick={handleAudio}
                  className="border-[3px] border-black bg-purple-400 px-4 py-2 text-black shadow-[4px_4px_0_0_#000000] transition-transform hover:-translate-x-0.5 hover:-translate-y-0.5 hover:bg-purple-300"
              >
                Download Explanation Audio
              </Button> */}
              {audioUrl ? (<>

              <WavesurferPlayer
                height={100}
                width={240}
                waveColor="violet"
                url={audioUrl}
                onReady={onReady}
                onPlay={() => setIsPlaying(true)}
                onPause={() => setIsPlaying(false)}
            />
            <div style={{ width: "10px" }}></div>
            <div className="py-4">
                <button onClick={onPlayPause} className="border-[3px] rounded-md font-medium border-black bg-orange-400 px-4 py-2 text-black shadow-[4px_4px_0_0_#000000] transition-transform hover:-translate-x-0.5 hover:-translate-y-0.5 hover:bg-orange-300">
                    {isPlaying ? 'Pause' : 'Play'}
                </button>
            </div>
            </>
            ) : (
              <Button
                onClick={handleAudio}
                className="border-[3px] border-black bg-orange-400 px-4 py-2 text-black shadow-[4px_4px_0_0_#000000] transition-transform hover:-translate-x-0.5 hover:-translate-y-0.5 hover:bg-orange-300"
              >
                Play Explanation Audio
              </Button>
            )}
          </div>
        )}

      </div>

      <ApiKeyDialog
        isOpen={showApiKeyDialog}
        onClose={handleCloseApiKeyDialog}
        onSubmit={handleApiKeySubmit}
        tokenCount={tokenCount}
      />
    </div>
  );
}