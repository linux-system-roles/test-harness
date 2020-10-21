#!/usr/bin/python3
import sys
import productmd.compose


def composeurl2images(
    composeurl, desiredarch, desiredvariant=None, desiredsubvariant=None
):
    # we will need to join it with a relative path component
    if composeurl.endswith("/"):
        composepath = composeurl
    else:
        composepath = composeurl + "/"

    compose = productmd.compose.Compose(composepath)

    candidates = set()

    for variant, arches in compose.images.images.items():
        for arch in arches:
            if arch == desiredarch:
                for image in arches[arch]:
                    if image.type == "qcow2":
                        candidates.add((image, variant, image.subvariant))

    # variant and subvariant are used only as a hint
    # to disambiguate if multiple images were found
    if len(candidates) > 1:
        if desiredvariant:
            variantmatch = {
                imginfo for imginfo in candidates if imginfo[1] == desiredvariant
            }
            if len(variantmatch) > 0:
                candidates = variantmatch
    if len(candidates) > 1:
        if desiredsubvariant:
            subvariantmatch = {
                imginfo for imginfo in candidates if imginfo[2] == desiredsubvariant
            }
            if len(subvariantmatch) > 0:
                candidates = subvariantmatch

    return [(composepath + qcow2[0].path) for qcow2 in candidates]


if __name__ == "__main__":
    USAGE = "Usage: %s <composeurl> <arch> <variant>" % sys.argv[0]

    # sanity-check arguments
    if len(sys.argv) != 4:
        print("Invalid arguments.")
        print(USAGE)
        sys.exit(2)

    composeurl = sys.argv[1]
    arch = sys.argv[2]
    variant = sys.argv[3]
    # subvariant could be added if needed
    imageurls = composeurl2images(composeurl, arch, variant)
    if len(imageurls) == 1:
        print(imageurls[0])
    else:
        sys.exit("multiple images found: {}".format(imageurls))
