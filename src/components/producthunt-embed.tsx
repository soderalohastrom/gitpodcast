import React from 'react';
import Image from 'next/image';

const ProductHuntEmbed = () => {
  return (
    <a
      href="https://www.producthunt.com/posts/gitpodcast?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_souce=badge-gitpodcast"
      target="_blank"
      rel="noopener noreferrer"
    >
      <Image
        src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=750368&theme=light&period=daily"
        alt="GitPodcast - Generate engaging podcast to understand a Github repo | Product Hunt"
        width={250}
        height={54}
      />
    </a>
  );
};

export default ProductHuntEmbed;