const Image = require("@11ty/eleventy-img")
const path = require('path')

module.exports = config => {
    // config.addPassthroughCopy('./src/assets');
    config.addPassthroughCopy("./src/pi7.css");
    config.addPassthroughCopy("./src/Inter-VariableFont_slnt,wght.ttf");

    	// --- START, eleventy-img
	function imageShortcode(src, alt, sizes="(min-width: 1024px) 100vw, 50vw") {
		console.log(`Generating image(s) from:  ${src}`)
        src = "./src/assets/img/" + src;
		let options = {
			widths: [600, 900, 1500],
			formats: ["webp", "jpeg"],
			urlPath: "/assets/img/",
			outputDir: "./dist/assets/img",
			filenameFormat: function (id, src, width, format, options) {
				const extension = path.extname(src)
				const name = path.basename(src, extension)
				return `${name}-${width}w.${format}`
			}
		}

		// generate images
		Image(src, options)

		let imageAttributes = {
			alt,
			sizes,
			loading: "lazy",
			decoding: "async",
		}
		// get metadata
		metadata = Image.statsSync(src, options)
		return Image.generateHTML(metadata, imageAttributes)
	}
	config.addShortcode("image", imageShortcode)
	// --- END, eleventy-img


    // Returns journal entries, in reverse chronological order.
    config.addCollection('journal', collection => {
        return [...collection.getFilteredByGlob('./src/journal/*.md')].reverse();
    });

    config.addCollection('allpages', collection => {
        return [...collection.getFilteredByGlob('./src/pages/*.*')];
    });

    config.addCollection('categories', collection => {
        return collection.getAll().filter(item => item.data.category);
    });

    config.addCollection('pagesByCategory', function (collection) {
        const pagesByCategory = {};

        collection.getAll().forEach((page) => {
            if (page.data.category) {
                category = page.data.category;
                if (!pagesByCategory[category]) {
                    pagesByCategory[category] = [];
                }
                pagesByCategory[category].push(page);
            };
        });

        // Sort pages within each category by date
        for (const category in pagesByCategory) {
            pagesByCategory[category].sort((a, b) => {
                return a.date - b.date;
            });
        }

        // console.log(pagesByCategory);

        return pagesByCategory;
    });

    return {
        markdownTemplateEngine: 'njk',
        dataTemplateEngine: 'njk',
        htmlTemplateEngine: 'njk',
        dir: {
            input: 'src',
            output: 'dist'
        }
    };
};
