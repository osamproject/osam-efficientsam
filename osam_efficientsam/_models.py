import numpy as np
from osam_core import apis
from osam_core import types


class EfficientSam(types.Model):
    def encode_image(self, image: np.ndarray) -> types.ImageEmbedding:
        if image.ndim == 2:
            raise ValueError("Grayscale images are not supported")
        if image.ndim == 3 and image.shape[2] == 4:
            raise ValueError("RGBA images are not supported")

        batched_images = image.transpose(2, 0, 1)[None].astype(np.float32) / 255
        image_embedding = self._inference_sessions["encoder"].run(
            output_names=None,
            input_feed={"batched_images": batched_images},
        )[0][0]  # (embedding_dim, height, width)

        return types.ImageEmbedding(
            original_height=image.shape[0],
            original_width=image.shape[1],
            embedding=image_embedding,
        )

    def generate_mask(
        self,
        image_embedding: types.ImageEmbedding,
        prompt: types.Prompt,
    ) -> np.ndarray:
        input_point = np.array(prompt.points, dtype=np.float32)
        input_label = np.array(prompt.point_labels, dtype=np.float32)

        # batch_size, embedding_dim, height, width
        batched_image_embedding = image_embedding.embedding[None, :, :, :]
        # batch_size, num_queries, num_points, 2
        batched_point_coords = input_point[None, None, :, :]
        # batch_size, num_queries, num_points
        batched_point_labels = input_label[None, None, :]

        decoder_inputs = {
            "image_embeddings": batched_image_embedding,
            "batched_point_coords": batched_point_coords,
            "batched_point_labels": batched_point_labels,
            "orig_im_size": np.array(
                (image_embedding.original_height, image_embedding.original_width),
                dtype=np.int64,
            ),
        }

        masks, _, _ = self._inference_sessions["decoder"].run(None, decoder_inputs)
        mask = masks[0, 0, 0, :, :]  # (1, 1, 3, H, W) -> (H, W)
        mask = mask > 0.0

        return mask


class EfficientSam10m(EfficientSam):
    name = "efficientsam:10m"

    _blobs = {
        "encoder": types.Blob(
            url="https://github.com/labelmeai/efficient-sam/releases/download/onnx-models-20231225/efficient_sam_vitt_encoder.onnx",
            hash="sha256:7a73ee65aa2c37237c89b4b18e73082f757ffb173899609c5d97a2bbd4ebb02d",
        ),
        "decoder": types.Blob(
            url="https://github.com/labelmeai/efficient-sam/releases/download/onnx-models-20231225/efficient_sam_vitt_decoder.onnx",
            hash="sha256:e1afe46232c3bfa3470a6a81c7d3181836a94ea89528aff4e0f2d2c611989efd",
        ),
    }


class EfficientSam25m(EfficientSam):
    name = "efficientsam:latest"

    _blobs = {
        "encoder": types.Blob(
            url="https://github.com/labelmeai/efficient-sam/releases/download/onnx-models-20231225/efficient_sam_vits_encoder.onnx",
            hash="sha256:4cacbb23c6903b1acf87f1d77ed806b840800c5fcd4ac8f650cbffed474b8896",
        ),
        "decoder": types.Blob(
            url="https://github.com/labelmeai/efficient-sam/releases/download/onnx-models-20231225/efficient_sam_vits_decoder.onnx",
            hash="sha256:4727baf23dacfb51d4c16795b2ac382c403505556d0284e84c6ff3d4e8e36f22",
        ),
    }


apis.register_model_type(EfficientSam10m)
apis.register_model_type(EfficientSam25m)
