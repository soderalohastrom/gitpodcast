"use client";

import { useParams } from "next/navigation";
import MainCard from "~/components/main-card";
import Loading from "~/components/loading";
import MermaidChart from "~/components/mermaid-diagram";
import { useDiagram } from "~/hooks/useDiagram";
import { ApiKeyDialog } from "~/components/api-key-dialog";
import { Button } from "~/components/ui/button";
import { ApiKeyButton } from "~/components/api-key-button";
import React, { useState, useEffect, useRef } from 'react';
import WavesurferPlayer  from '@wavesurfer/react'
import WaveSurfer from 'wavesurfer.js';


export default function Repo() {
    const [wavesurfer, setWavesurfer] = useState<WaveSurfer | null>(null);
    const [isPlaying, setIsPlaying] = useState(false)
    const [gradient, setGradient] = useState<CanvasGradient | null>(null);
    const [progressGradient, setProgressGradient] = useState<CanvasGradient | null>(null);
    const videoRef = useRef<HTMLVideoElement | null>(null);
    const subtitleRef = useRef<HTMLDivElement>(null);



    const onReady = (ws: any) => {
        setWavesurfer(ws)
        setIsPlaying(false)
    }
    const onPlayPause = () => {


        if(isPlaying) {
            videoRef.current?.pause();
        } else {
            videoRef.current?.play();
            console.log("now playing")
        }

        wavesurfer && wavesurfer.playPause()


    }

    useEffect(() => {
        const canvas = document.createElement('canvas');

        // Ensure the canvas has dimensions, otherwise ctx will be null
        canvas.width = 100; // or any non-zero value
        canvas.height = 100; // or any non-zero value

        const ctx = canvas.getContext('2d');

        if (ctx) {
            // Define the waveform gradient
            const tempGradient = ctx.createLinearGradient(0, 0, 0, canvas.height * 1.35);
            tempGradient.addColorStop(0, '#656666'); // Top color
            tempGradient.addColorStop((canvas.height * 0.7) / canvas.height, '#656666'); // Top color
            tempGradient.addColorStop((canvas.height * 0.7 + 1) / canvas.height, '#ffffff'); // White line
            tempGradient.addColorStop((canvas.height * 0.7 + 2) / canvas.height, '#ffffff'); // White line
            tempGradient.addColorStop((canvas.height * 0.7 + 3) / canvas.height, '#B1B1B1'); // Bottom color
            tempGradient.addColorStop(1, '#B1B1B1'); // Bottom color

            setGradient(tempGradient);

            // Define the progress gradient
            const tempProgressGradient = ctx.createLinearGradient(0, 0, 0, canvas.height * 1.35);
            tempProgressGradient.addColorStop(0, '#EE772F'); // Top color
            tempProgressGradient.addColorStop((canvas.height * 0.7) / canvas.height, '#EB4926'); // Top color
            tempProgressGradient.addColorStop((canvas.height * 0.7 + 1) / canvas.height, '#ffffff'); // White line
            tempProgressGradient.addColorStop((canvas.height * 0.7 + 2) / canvas.height, '#ffffff'); // White line
            tempProgressGradient.addColorStop((canvas.height * 0.7 + 3) / canvas.height, '#F6B094'); // Bottom color
            tempProgressGradient.addColorStop(1, '#F6B094'); // Bottom color

            setProgressGradient(tempProgressGradient);
        }
    }, []); // Empty dependency array ensures this effect runs only once, akin to componentDidMount


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
    audioRef,
    subtitleUrl
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

              {audioUrl ? (
            <div>
                <video ref={videoRef} id="audioVideo"  height={360} width={380} controls crossOrigin="anonymous">
                    <source src={audioUrl} type="audio/mp3" />
                    <track src={subtitleUrl} kind="subtitles" label="English" srcLang="en" default/>
                </video>
            </div>

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