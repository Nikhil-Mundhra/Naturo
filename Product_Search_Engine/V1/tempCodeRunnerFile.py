    parsed = parse_product_code(code)
        supplier = parsed["supplier"]
        folder_code = parsed["folder_code"]
        materials = [normalize_token(m) for m in parsed["material"]]
        colors = [normalize_token(c) for c in parsed["color"]]
        sizes = parsed["size"]
        file_token = parsed["file_token"]

        search_node = self.tree
        sup_node = None
        if supplier:
            sup_node = self.find_supplier_selected_folder(supplier)
            if sup_node:
                search_node = sup_node

        fc_node = None
        if folder_code and search_node:
            fc_node = self.find_folder_with_code(search_node, folder_code, supplier_prefix=supplier)
            if fc_node:
                search_node = fc_node

        allow_images = True
        final_node, stop_reason = self.descend_to_images_or_branch(search_node, folder_code, allow_images=allow_images)

        node_for_scan = final_node or search_node
        candidate_files = self.collect_candidate_files(node_for_scan)
        base_root = node_for_scan.get("_path") if node_for_scan else self.root_dir

        series_signatures = extract_series_signatures(code)

        matches, reasons = [], []
        for p in candidate_files:
            rel = os.path.relpath(p, base_root) if base_root else os.path.basename(p)
            s = make_searchable(rel)

            # Fast-path override
            if path_contains_any_signature(rel, series_signatures):
                matches.append(p)
                continue

            fail = []
            if materials and not any(m in s for m in materials):
                fail.append("material")
            if colors and not color_matches(s, colors):
                fail.append("color")
            if sizes and not matches_size(s, sizes):
                fail.append("size")
            if not file_token_match(s, file_token):
                fail.append("file_token")
            if fail:
                reasons.append((p, fail))
            else:
                matches.append(p)

        debug = {
            "parsed": parsed,
            "initial_root": self.root_dir,
            "supplier_folder_found": sup_node.get("_path") if sup_node else None,
            "folder_code_folder_found": fc_node.get("_path") if fc_node else None,
            "autodescent_final_root": (final_node or search_node).get("_path") if (final_node or search_node) else None,
            "autodescent_stop_reason": stop_reason,
            "candidate_count": len(candidate_files),
            "matches_count": len(matches),
            "matches": matches[:max_show],
            "rejections": reasons[:max_show]
        }
        return debug, matches